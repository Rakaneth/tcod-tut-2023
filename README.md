# Roguelike Dev Tutorial 2023

This is my entry for [r/roguelikedev's](https://reddit.com/r/roguelikedev) annual tutorial event. It is a ~~overdone~~ classic medieval fantasy roguelike set in a world of my own design.

# Progress

* [x] Part 0 - Setting Up
* [x] Part 1 - Drawing the '@' symbol and moving it around
* [x] Part 2 - The generic Entity, the render functions, and the map
* [x] Part 3 - Generating a dungeon
* [ ] Part 4 - Field of view
* [ ] Part 5 - Placing enemies and kicking them (harmlessly)
* [ ] Part 6 - Doing (and taking) some damage
* [ ] Part 7 - Creating the interface
* [ ] Part 8 - Items and Inventory
* [ ] Part 9 - Ranged Scrolls and Targeting
* [ ] Part 10 - Saving and loading
* [ ] Part 11 - Delving into the Dungeon
* [ ] Part 12 - Increasing Difficulty
* [ ] Part 13 - Gearing up

# Libraries used

[tcod](https://github.com/libtcod/python-tcod), [tcod-ecs](https://github.com/HexDecimal/python-tcod-ecs), pyyaml

# DevLog

## Week 2

More plumbing. With a little bit of refactoring, there is now a module that stores components and a module that will create entities with all the required components. I have decided on using a YAML file (for which I am using the PyYAML library) to store the game data; I find it much easier to quickly edit and read a YAML file than a Python dictionary. I've also decided on a smaller screen size with a large 32x32 font.

Created several modules for drawing and the map. I originally wanted to have a lighter map class that would convert raw tile data - ints, at first - to the proper graphics data when the map was drawn, but I had trouble getting NumPy to play nicely with broadcasting tuple data, so I opted for the method used in the most recent tcod tutorial - with a modification that allows for large, scrolling maps. There is a `Camera` object that keeps track of a viewport, and the `draw_map` function in `ui.py` uses it to draw everything around the player. 

Using `tcod-ecs`'s relations feature, I was able to filter out entities not on the map being drawn. This is a huge step in being able to keep 100% of the game state - including maps - in a single `World`, which will make part 10 much easier. 

This nearly completes Week 2, though I still need to figure out how to get the game maps themselves as a resource that the `World` can use - and I need to stop the player from going out of the map bounds.

## Week 1

I've done a bit of plumbing, setting up an `Engine` class to hold the game state and run the game, as well, as a system of `Screen`s that are responsible for handling their own inputs. This will come in handy down the road when I implement things like equipment and shop menus. I've also added `bootstrap.sh` and `bootstrap.bat` to quickly get the virtual environment and dependencies installed. Running the game from a fresh start should be as simple as:

1. `git clone https://github.com/Rakaneth/tcod-tut-2023`
2. `sh bootstrap.sh` (Linux) or  `.\bootstrap.bat` (Windows)
3. `. ./env/bin/activate` (Linux) or `.\env\Scripts\activate` (Windows)
4. `python main.py`

In addition, a minimal Python debug config file for VSCode is included. With Microsoft's Python extension installed, select the Python interpreter in the `./env` folder and then the game can be debugged with `F5`.

Got started early using the brand-spanking-new `tcod-ecs`, which I find less annoying to use than `esper`. There is a bit of a learning curve, but I was able to use it to make a generic entity that could move around and produce the famous `@`.

With that, Week 1 is done. I will try to avoid skipping ahead, but that means I might make a second project alongside this to continue playing with `tcod-ecs`.