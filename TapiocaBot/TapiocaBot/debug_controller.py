class DebugController:
    def __init__(self, bot=None, verbose=False):
        self.bot = bot
        self.verbose = verbose

        self.current_y = 0
        self.y_inc = 0.018

        self.font_size = 14

    def debug_text_screen(self, message):
        self.bot._client.debug_text_screen(
            message,
            pos=(0.001, self.current_y),
            size=self.font_size
        )
        self.current_y += self.y_inc

    async def send(self):
        await self.bot._client.send_debug()
        self.current_y = 0
