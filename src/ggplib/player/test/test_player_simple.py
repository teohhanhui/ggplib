from ggplib.player import get
from ggplib.player.gamemaster import GameMaster
from ggplib.db import lookup

import pytest


def setup():
    from ggplib.util.init import setup_once
    setup_once()


def test_tictactoe_play():
    gm = GameMaster(lookup.by_name("ticTacToe"))

    # add two python players
    gm.add_player(get.get_player("pyrandom"), "xplayer")
    gm.add_player(get.get_player("pylegal"), "oplayer")

    gm.start(meta_time=10, move_time=5)
    gm.play_to_end()

    # check scores/depth make some sense
    assert sum(gm.scores.values()) == 100
    assert 5 <= gm.get_game_depth() <= 9


def test_tictactoe_play_verbose():
    gm = GameMaster(lookup.by_name("ticTacToe"), verbose=True)

    # add two python players
    gm.add_player(get.get_player("pyrandom"), "xplayer")
    gm.add_player(get.get_player("pylegal"), "oplayer")

    gm.start(meta_time=10, move_time=5)
    gm.play_to_end()

    # check scores/depth make some sense
    assert sum(gm.scores.values()) == 100
    assert 5 <= gm.get_game_depth() <= 9


def test_tictactoe_cpp_play():
    gm = GameMaster(lookup.by_name("ticTacToe"))

    # add two c++ players
    gm.add_player(get.get_player("random"), "xplayer")
    gm.add_player(get.get_player("legal"), "oplayer")

    gm.start(meta_time=10, move_time=5)
    gm.play_to_end()

    # check scores/depth make some sense
    assert sum(gm.scores.values()) == 100
    assert 5 <= gm.get_game_depth() <= 9


def test_tictactoe_take_win():
    gm = GameMaster(lookup.by_name("ticTacToe"))

    # add two c++ players
    gm.add_player(get.get_player("ggtest1"), "xplayer")
    gm.add_player(get.get_player("ggtest1"), "oplayer")

    str_state = '''
    (true (control xplayer))
    (true (cell 2 2 x))
    (true (cell 3 2 o))
    (true (cell 3 3 x))
    (true (cell 2 3 o))
    (true (cell 3 1 b))
    (true (cell 2 1 b))
    (true (cell 1 3 b))
    (true (cell 1 2 b))
    (true (cell 1 1 b)) '''

    gm.start(meta_time=30, move_time=2,
             initial_basestate=gm.convert_to_base_state(str_state))

    # play a single move - should take win
    move = gm.play_single_move()
    assert str(move[0]) == "(mark 1 1)"
    assert str(move[1]) == "noop"

    gm.play_to_end(last_move=move)

    # check scores/depth make some sense
    assert gm.scores['xplayer'] == 100
    assert gm.scores['oplayer'] == 0
    assert gm.get_game_depth() == 1


@pytest.mark.slow
def test_breakthrough():
    ' mcs player vs ggtest1 '
    gm = GameMaster(lookup.by_name("breakthrough"))

    # add two players
    white = get.get_player("pymcs")
    white.max_run_time = 0.25

    black = get.get_player("simplemcts")
    black.skip_single_moves = True

    gm.add_player(white, "white")
    gm.add_player(black, "black")

    gm.start(meta_time=30, move_time=2.0)
    gm.play_to_end()

    # hopefully simplemcts wins!  Not a great test.
    assert gm.scores["white"] == 0
    assert gm.scores["black"] == 100

    # check scores/depth make some sense
    assert sum(gm.scores.values()) == 100
    assert gm.get_game_depth() >= 10


def test_not_in_db():
    some_simple_game = """
  (role white)
  (role black)

  (init o1)

  (legal white a)
  (legal white b)
  (legal black a)

  (<= (next o2) (does white a) (true o1))
  (<= (next o3) (does white b) (true o1))

  (<= (goal white 0) (true o1))
  (<= (goal white 10) (true o2))
  (<= (goal white 90) (true o3))

  (<= (goal black 0) (true o1))
  (<= (goal black 90) (true o2))
  (<= (goal black 10) (true o3))

  (<= terminal (true o2))
  (<= terminal (true o3))
    """

    _, game_info = lookup.by_gdl(some_simple_game)
    gm = GameMaster(game_info)

    # add two python players
    gm.add_player(get.get_player("pyrandom"), "black")
    gm.add_player(get.get_player("ggtest1"), "white")

    gm.start(meta_time=10, move_time=5)
    gm.play_to_end()


def test_speed():
    gm = GameMaster(lookup.by_name("reversi"))

    # add two python players
    a = get.get_player("simplemcts")
    a.skip_single_moves = True
    a.max_tree_playout_iterations = 200

    b = get.get_player("simplemcts")
    b.skip_single_moves = True
    b.max_tree_playout_iterations = 200

    gm.add_player(a, "red")
    gm.add_player(b, "black")

    import time
    gm.start(meta_time=10, move_time=5)
    s = time.time()
    gm.play_to_end()
    print "DONE", time.time() - s
