import discord
import feedparser
import requests
from collections import deque
from contextlib import suppress
from discord.ext import commands

class Nyaa:

	def __init__(self, bot):
		self.bot = bot
		self.host = "https://nyaa.si"

	# prioritize English results
	@commands.command(pass_context=True, no_pm=False)
	async def nyaa(self, ctx, *, title):
		await self.search(ctx, title, eng=True)

	# prioritize latest results
	@commands.command(pass_context=True, no_pm=False)
	async def nyaall(self, ctx, *, title):
		await self.search(ctx, title, eng=False)

	# search trusted > non-remakes > english anime > all torrents
	# skip to all torrents if nyaall
	async def getfeed(self, title, eng):
		feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0"

		rss = "&page=rss"

		everything = self.host + "/?q=" + title
		filters    = deque()
		filters.append(('trusted',   everything + "&c=1_2&f=2"))
		filters.append(('no_remake', everything + "&c=1_2&f=1"))
		filters.append(('english',   everything + "&c=1_2&f=0"))
		
		if eng:
			for f in filters:
				feed = feedparser.parse(f[1]+rss, referrer=f[1])
				if feed["bozo"] == 0 and len(feed["items"]) > 0:
					return feed

		return feedparser.parse(everything+rss, referrer=everything)

	# requests.get() throws due to lack of context adapter for magnet links
	# just parsing it from the exception message NBD fam
	async def getmagnet(self, item):
		magnet=""
		try:
			magnet = requests.get(item["guid"]+"/magnet").url
		except Exception as e:
			with suppress(Exception):
				magnet = str(e)[str(e).find('magnet:'):].strip("'")
		return magnet

	async def search(self, ctx, title, eng):
		feed = await self.getfeed(title=title, eng=eng)

		if feed["bozo"] == 1:
			await self.bot.say("Invalid feed.")
			return

		items = feed["items"]

		if len(items) < 1:
			await self.bot.say("No matching torrents found.")
			return

		item = items[0]

		request = ctx.message
		requester = request.author

		magnet = await self.getmagnet(item)

		embed = discord.Embed(colour=requester.color if hasattr(requester, 'color') else 0x0066FF,
			                  description="[:inbox_tray: Torrent]({}) [:link: Magnet]({})\n".format(
			                              	item["link"], magnet))
		embed.title = item["title"]
		embed.url = item["guid"]
		embed.set_thumbnail(url="{}/static/img/icons/nyaa/{}.png".format(self.host, item["nyaa_categoryid"]))
		embed.set_author(name='{} ／ {}'.format(requester.display_name, requester.name),
			             icon_url=requester.avatar_url if requester.avatar else requester.default_avatar_url)
		embed.set_footer(text="{} | {}".format(item["nyaa_size"], item["nyaa_category"]))

		await self.bot.say(embed=embed)

		# dunno how to check if we're in a DM, so don't throw perms error
		with suppress(discord.errors.Forbidden):
			await self.bot.delete_message(request)

def setup(bot):
	bot.add_cog(Nyaa(bot))
