import time
import random
from pprint import pprint

import py

from ggplib.db import lookup

from ggplib.non_gdl_games.draughts import desc


# unskip to run all tests, but it will take ages.
skip_slow = True


def setup():
    from ggplib.util.init import setup_once
    setup_once(__file__)


def test_create_id_10():
    board_desc = desc.BoardDesc(10)

    info = lookup.by_name("draughts_bt_10x10")

    # will dupe / and reset
    sm = info.get_sm()

    joint_move = sm.get_joint_move()
    base_state = sm.new_base_state()

    base_state.assign(sm.get_current_state())

    desc.print_board(board_desc, base_state)
    pprint(info.model.basestate_to_str(base_state))

    while not sm.is_terminal():
        print "==============="
        print "Dumping legals:"
        print "==============="

        for role_index, role in enumerate(sm.get_roles()):
            ls = sm.get_legal_state(role_index)
            print role, [sm.legal_to_move(role_index, ls.get_legal(ii)) for ii in range(ls.get_count())]

        print
        print "** Choose a random move for each role:"
        for role_index, role in enumerate(sm.get_roles()):
            ls = sm.get_legal_state(role_index)
            choice = ls.get_legal(random.randrange(0, ls.get_count()))
            joint_move.set(role_index, choice)
            print "    %s :" % role, sm.legal_to_move(role_index, choice)
        print

        # play move, the base_state will be new state
        sm.next_state(joint_move, base_state)

        # update the state machine to new state
        sm.update_bases(base_state)

        desc.print_board(board_desc, base_state)


def test_speed():
    for game in ("draughts_bt_10x10", "draughts_killer_10x10"):

        info = lookup.by_name(game)

        # will dupe / and reset
        sm = info.get_sm()

        joint_move = sm.get_joint_move()
        base_state = sm.new_base_state()
        role_count = len(sm.get_roles())

        all_scores = [[] for i in range(role_count)]

        s = time.time()
        ITERATIONS = 100
        total_depth = 0
        for ii in range(ITERATIONS):
            sm.reset()

            while not sm.is_terminal():
                for role_index, role in enumerate(sm.get_roles()):
                    ls = sm.get_legal_state(role_index)
                    choice = ls.get_legal(random.randrange(0, ls.get_count()))
                    joint_move.set(role_index, choice)

                # play move, the base_state will be new state
                sm.next_state(joint_move, base_state)

                # update the state machine to new state
                sm.update_bases(base_state)
                total_depth += 1

            for ri in range(role_count):
                all_scores[ri].append(sm.get_goal_value(ri))

        total_time = time.time() - s

        print all_scores
        print "average depth", total_depth / float(ITERATIONS)
        print (total_time / float(ITERATIONS)) * 1000

        print "running %s for 2 seconds in c" % game
        from ggplib.interface import depth_charge

        msecs_taken, rollouts, num_state_changes = depth_charge(sm, 2)

        print "===================================================="
        print "ran for %.3f seconds, state changes %s, rollouts %s" % ((msecs_taken / 1000.0),
                                                                       num_state_changes,
                                                                       rollouts)
        print "rollouts per second: %s" % (rollouts / (msecs_taken / 1000.0))


def create_player():
    from ggplib.player import get
    player = get.get_player("simplemcts")
    player.max_tree_search_time = 0.25
    player.skip_single_moves = True
    player.dump_depth = 1
    return player


def test_play():
    if skip_slow:
        py.test.skip("too slow")

    from ggplib.player.gamemaster import GameMaster

    game_info = lookup.by_name("draughts_killer_10x10")
    gm = GameMaster(game_info, verbose=False)

    # add two python players
    gm.add_player(create_player(), "white")
    gm.add_player(create_player(), "black")

    gm.start(meta_time=2, move_time=2)
    gm.play_to_end()

    # check scores/depth make some sense
    print gm.scores


def dump_legals(sm):
    print "==============="
    print "Dumping legals:"
    print "==============="

    for role_index, role in enumerate(sm.get_roles()):
        ls = sm.get_legal_state(role_index)
        print role, [sm.legal_to_move(role_index, ls.get_legal(ii)) for ii in range(ls.get_count())]


def random_move(sm):
    joint_move = sm.get_joint_move()
    base_state = sm.new_base_state()

    for role_index, role in enumerate(sm.get_roles()):
        ls = sm.get_legal_state(role_index)
        choice = ls.get_legal(random.randrange(0, ls.get_count()))
        joint_move.set(role_index, choice)
        print "playing    %s :" % role, sm.legal_to_move(role_index, choice)
    print

    # play move, the base_state will be new state
    sm.next_state(joint_move, base_state)

    # update the state machine to new state
    sm.update_bases(base_state)


def test_captures_king():
    fen = "W:WK48:B31,42,21,22,19,10,39,29"

    board_desc = desc.BoardDesc(10)
    sm = desc.create_board(board_desc, fen)

    base_state = sm.new_base_state()

    desc.print_board(board_desc, base_state)

    base_state.assign(sm.get_current_state())

    for i in range(7):
        desc.print_board(board_desc, base_state)
        dump_legals(sm)

        if sm.is_terminal():
            break

        # random move
        random_move(sm)
        base_state.assign(sm.get_current_state())


def test_captures_king2():
    fen = "W:WK48:B31,42,21,22,19,10,39,29"

    board_desc = desc.BoardDesc(10)
    sm = desc.create_board(board_desc, fen)

    base_state = sm.new_base_state()

    base_state.assign(sm.get_current_state())

    for i in range(7):
        desc.print_board(board_desc, base_state)
        dump_legals(sm)

        if sm.is_terminal():
            print "AND DONE"
            break

        # random move
        random_move(sm)
        base_state.assign(sm.get_current_state())
