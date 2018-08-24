from s2clientprotocol import (
    sc2api_pb2 as sc_pb,
    common_pb2 as common_pb,
    query_pb2 as query_pb,
    debug_pb2 as debug_pb,
    raw_pb2 as raw_pb,
)


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

    async def debug_destroy_unit(self, unit_tag):
        await self.bot._client._execute(
            debug=sc_pb.RequestDebug(
                debug=[
                    debug_pb.DebugCommand(
                        kill_unit=debug_pb.DebugKillUnit(
                            tag=[unit_tag]
                        )
                    )
                ]
            )
        )

    async def send(self):
        await self.bot._client.send_debug()
        self.reset()

    def reset(self):
        # await self.bot._client.send_debug()
        self.current_y = 0
