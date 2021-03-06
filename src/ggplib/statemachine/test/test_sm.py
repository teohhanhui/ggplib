from ggplib.util import log
from ggplib.propnet import getpropnet
from ggplib.statemachine.forwards import FwdStateMachine
from ggplib.statemachine import builder
from ggplib import interface
from ggplib.statemachine.depthcharges import depth_charges

from ggplib.db import helper

def setup():
    from ggplib.util.init import setup_once
    setup_once()


def test_get_by_propnet_name():
    ''' legacy test '''
    games = ["ticTacToe", "connectFour", "breakthrough", "speedChess"]
    propnets1 = [getpropnet.get_with_game(g) for g in games]
    propnets2 = [getpropnet.get_with_game(g) for g in games]

    for p1, p2 in zip(propnets1, propnets2):
        # these will be ordered
        assert p1.get_initial_state() == p2.get_initial_state()


def test_python_statemachine():
    ''' legacy test '''
    games = ["ticTacToe", "connectFour", "breakthrough", "speedChess"]
    propnets1 = [getpropnet.get_with_game(g) for g in games]
    propnets2 = [getpropnet.get_with_game(g) for g in games]

    state_machines1 = [FwdStateMachine(propnet) for propnet in propnets1]
    state_machines2 = [FwdStateMachine(propnet) for propnet in propnets2]

    for sm1, sm2 in zip(state_machines1, state_machines2):
        sm1.reset()
        sm2.reset()
        assert sm1.propnet.roles == sm2.propnet.roles

        # check legals the same for both roles
        for role_info1, role_info2 in zip(sm1.propnet.role_infos, sm1.propnet.role_infos):
            assert role_info1.role == role_info2.role
            assert sm1.get_legal_moves(role_info1) == sm2.get_legal_moves(role_info2)


def create_and_play(sm):
    assert len(sm.get_roles()) == 2

    sm.reset()
    assert sm.get_initial_state()
    ls = sm.get_legal_state(0)

    # 9 possible moves initially
    assert ls.get_count() == 9

    def f(ri, i):
        return sm.legal_to_move(ri, ls.get_legal(i))

    moves = [f(0, ii) for ii in range(ls.get_count())]
    assert "(mark 2 2)" in moves

    play_moves = [("(mark 2 2)", "noop"),
                  ("noop", "(mark 3 3)"),
                  ("(mark 2 3)", "noop"),
                  ("noop", "(mark 1 1)"),
                  ("(mark 2 1)", "noop")]

    # get some states
    joint_move = sm.get_joint_move()
    base_state = sm.new_base_state()

    for move in play_moves:
        assert not sm.is_terminal()

        log.info("Playing %s" % (move,))
        for ri in range(len(sm.get_roles())):
            ls = sm.get_legal_state(ri)
            the_moves = [f(ri, ii) for ii in range(ls.get_count())]
            log.verbose("%s moves %s" % (sm.get_roles()[ri], the_moves))
            choice = the_moves.index(move[ri])
            joint_move.set(ri, ls.get_legal(choice))

        # update state machine
        sm.next_state(joint_move, base_state)
        sm.update_bases(base_state)

    assert sm.is_terminal()
    assert sm.get_goal_value(0) == 100
    assert sm.get_goal_value(1) == 0


def test_create_and_play_with_standard_sm():
    ' plays a simple game of tictactoe, ensuring correct states throughtout'
    gdl_str = helper.get_gdl_for_game("ticTacToe")
    _, sm = builder.build_sm(gdl_str,
                             no_goalless=True, try_combined=False)
    create_and_play(sm)


def test_create_and_play_with_goalless_sm():
    ' plays a simple game of tictactoe, ensuring correct states throughtout'
    gdl_str = helper.get_gdl_for_game("ticTacToe")
    _, sm = builder.build_sm(gdl_str, try_combined=False)
    create_and_play(sm)


def test_create_and_play_with_sm_combined():
    ' plays a simple game of tictactoe, ensuring correct states throughtout'
    gdl_str = helper.get_gdl_for_game("ticTacToe")
    _, sm = builder.build_sm(gdl_str, try_combined=True)
    create_and_play(sm)


def test_dupes_deallocs():
    def go(gdl_str):
        _, sm = builder.build_sm(gdl_str)

        sm.reset()

        sm2 = sm.dupe()
        interface.dealloc_statemachine(sm)
        sm2.reset()

        log.info("Doing depth charges on %s" % sm2)
        msecs_taken, rollouts, _ = interface.depth_charge(sm2, 2)
        rollouts_per_second = (rollouts / float(msecs_taken)) * 1000
        log.info("rollouts per second %.2f" % rollouts_per_second)

        # test from python
        depth_charges(sm2, 1)

        interface.dealloc_statemachine(sm2)

    for game in ("ticTacToe", "connectFour", "breakthrough"):
        gdl_str = helper.get_gdl_for_game(game)
        go(gdl_str)
