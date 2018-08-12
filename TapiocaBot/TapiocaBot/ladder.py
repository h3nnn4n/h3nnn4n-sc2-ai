# pylint: disable=C0301

import argparse
import sys
import asyncio
import logging
import aiohttp
import sc2
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer
from sc2.sc2process import SC2Process
from sc2.client import Client


def run_ladder_game(bot):
    parser = argparse.ArgumentParser()
    parser.add_argument('--GamePort', type=int, nargs="?", help='Game port')
    parser.add_argument('--StartPort', type=int, nargs="?", help='Start port')
    parser.add_argument('--LadderServer', type=str, nargs="?", help='Ladder server')
    parser.add_argument('--ComputerOpponent', type=str, nargs="?", help='Computer opponent')
    parser.add_argument('--ComputerRace', type=str, nargs="?", help='Computer race')
    parser.add_argument('--ComputerDifficulty', type=str, nargs="?", help='Computer difficulty')
    parser.add_argument('--OpponentId', type=str, nargs="?", help='Opponent ID')
    args, _ = parser.parse_known_args()

    if args.LadderServer is None:
        host = "127.0.0.1"
    else:
        host = args.LadderServer

    host_port = args.GamePort
    lan_port = args.StartPort

    ports = [lan_port + p for p in range(1, 6)]

    portconfig = sc2.portconfig.Portconfig()
    portconfig.shared = ports[0]  # Not used
    portconfig.server = [ports[1], ports[2]]
    portconfig.players = [[ports[3], ports[4]]]

    g = join_ladder_game(
        host=host,
        port=host_port,
        players=[bot],
        realtime=False,
        portconfig=portconfig
    )

    result = asyncio.get_event_loop().run_until_complete(g)
    print(result)


async def join_ladder_game(host, port, players, realtime, portconfig, save_replay_as=None, step_time_limit=None, game_time_limit=None):
    ws_url = "ws://{}:{}/sc2api".format(host, port)
    ws_connection = await aiohttp.ClientSession().ws_connect(ws_url, timeout=120)
    client = Client(ws_connection)

    try:
        result = await sc2.main._play_game(players[0], client, realtime, portconfig, step_time_limit, game_time_limit)
        if save_replay_as is not None:
            await client.save_replay(save_replay_as)
        await client.leave()
        await client.quit()
    except ConnectionAlreadyClosed:  # Where is this defined?
        logging.error(f"Connection was closed before the game ended")
        return None
    finally:
        ws_connection.close()

    return result
