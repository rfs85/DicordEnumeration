from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from .base import BaseEnumerator
import discord
from discord.ext import commands
import json
import logging
from datetime import datetime

class ServerEnumerator(BaseEnumerator):
    def __init__(self, token: Optional[str] = None):
        super().__init__(token)
        self.intents = discord.Intents.default()
        self.intents.guilds = True
        self.intents.members = True
        self.bot = commands.Bot(command_prefix="!", intents=self.intents)
        
    async def enumerate(self) -> Dict[str, Any]:
        results = {
            'timestamp': datetime.now().isoformat(),
            'servers': [],
            'invite_links': [],
            'public_servers': [],
            'server_statistics': {},
            'roles_info': {},
            'channels_info': {},
            'server_features': {},
            'verification_levels': {},
            'member_counts': {},
            'errors': []
        }
        
        try:
            if not self.token:
                self.logger.info("Running unauthenticated server enumeration...")
                await self._enumerate_public_servers(results)
            else:
                self.logger.info("Running authenticated server enumeration...")
                await self._enumerate_authenticated_servers(results)
        except Exception as e:
            error_msg = f"Error during enumeration: {str(e)}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
            
        return results
    
    async def _enumerate_public_servers(self, results: Dict[str, Any]):
        """
        Enumerate public Discord servers using various discovery methods
        """
        popular_categories = ['gaming', 'music', 'education', 'science', 'technology', 'anime', 
                            'entertainment', 'community', 'creative']
        
        async with aiohttp.ClientSession() as session:
            for category in popular_categories:
                try:
                    # Discord Discovery API endpoint
                    url = f"https://discord.com/api/v9/discovery/categories/{category}/guilds"
                    async with session.get(url, headers=self._get_headers()) as response:
                        if response.status == 200:
                            data = await response.json()
                            for server in data.get('guilds', []):
                                server_info = {
                                    'id': server.get('id'),
                                    'name': server.get('name'),
                                    'description': server.get('description'),
                                    'member_count': server.get('approximate_member_count'),
                                    'online_count': server.get('approximate_presence_count'),
                                    'features': server.get('features', []),
                                    'category': category,
                                    'discovery_splash': server.get('discovery_splash'),
                                    'preferred_locale': server.get('preferred_locale'),
                                    'vanity_url_code': server.get('vanity_url_code')
                                }
                                results['public_servers'].append(server_info)
                                self.logger.debug(f"Found public server: {server_info['name']}")
                except Exception as e:
                    error_msg = f"Error enumerating public servers for category {category}: {str(e)}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)

    async def _enumerate_authenticated_servers(self, results: Dict[str, Any]):
        """
        Enumerate servers using authenticated Discord bot/user token
        """
        try:
            client = discord.Client(intents=self.intents)
            
            @client.event
            async def on_ready():
                try:
                    self.logger.info(f"Logged in as {client.user.name}")
                    for guild in client.guilds:
                        try:
                            server_info = await self._gather_guild_info(guild)
                            results['servers'].append(server_info)
                            self.logger.debug(f"Enumerated server: {server_info['name']}")
                        except Exception as e:
                            error_msg = f"Error gathering info for guild {guild.id}: {str(e)}"
                            self.logger.error(error_msg)
                            results['errors'].append(error_msg)
                finally:
                    await client.close()
            
            await client.start(self.token)
            
        except Exception as e:
            error_msg = f"Error in authenticated enumeration: {str(e)}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
            
    async def _gather_guild_info(self, guild: discord.Guild) -> Dict[str, Any]:
        """
        Gather detailed information about a specific guild
        """
        server_info = {
            'id': str(guild.id),
            'name': guild.name,
            'owner_id': str(guild.owner_id),
            'created_at': guild.created_at.isoformat() if guild.created_at else None,
            'member_count': guild.member_count,
            'features': list(guild.features),
            'verification_level': str(guild.verification_level),
            'explicit_content_filter': str(guild.explicit_content_filter),
            'default_notifications': str(guild.default_notifications),
            'vanity_url_code': guild.vanity_url_code,
            'description': guild.description,
            'premium_tier': guild.premium_tier,
            'premium_subscription_count': guild.premium_subscription_count,
            'preferred_locale': str(guild.preferred_locale),
            'roles': [],
            'channels': [],
            'emojis': [],
            'member_statistics': {}
        }
        
        # Gather roles information
        for role in guild.roles:
            role_info = {
                'id': str(role.id),
                'name': role.name,
                'permissions': str(role.permissions),
                'color': str(role.color),
                'hoist': role.hoist,
                'position': role.position,
                'managed': role.managed,
                'mentionable': role.mentionable,
                'member_count': len(role.members)
            }
            server_info['roles'].append(role_info)
        
        # Gather channels information
        for channel in guild.channels:
            channel_info = {
                'id': str(channel.id),
                'name': channel.name,
                'type': str(channel.type),
                'category': str(channel.category) if channel.category else None,
                'position': channel.position,
                'created_at': channel.created_at.isoformat() if channel.created_at else None,
                'permissions_synced': getattr(channel, 'permissions_synced', None)
            }
            server_info['channels'].append(channel_info)
        
        # Gather emoji information
        for emoji in guild.emojis:
            emoji_info = {
                'id': str(emoji.id),
                'name': emoji.name,
                'animated': emoji.animated,
                'available': emoji.available,
                'url': str(emoji.url)
            }
            server_info['emojis'].append(emoji_info)
        
        # Gather member statistics
        member_stats = {
            'total': guild.member_count,
            'online': len([m for m in guild.members if m.status != discord.Status.offline]),
            'bots': len([m for m in guild.members if m.bot]),
            'roles_distribution': {role.name: len(role.members) for role in guild.roles}
        }
        server_info['member_statistics'] = member_stats
        
        return server_info

    async def _check_server_availability(self, server_id: str) -> Dict[str, Any]:
        """
        Check if a server is available and gather basic information
        """
        url = f"https://discord.com/api/v9/guilds/{server_id}/preview"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                return None 