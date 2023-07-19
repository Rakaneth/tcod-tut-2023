# Roguelike Dev Tutorial 2023

This is my entry for [r/roguelikedev's](https://reddit.com/r/roguelikedev) annual tutorial event. It is a ~~overdone~~ classic medieval fantasy roguelike set in a world of my own design.

# Progress

* [x] Part 0 - Setting Up
* [x] Part 1 - Drawing the '@' symbol and moving it around
* [x] Part 2 - The generic Entity, the render functions, and the map
* [x] Part 3 - Generating a dungeon
* [x] Part 4 - Field of view
* [x] Part 5 - Placing enemies and kicking them (harmlessly)
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

## Week 3

Implemented field of view and basic collision detection. I adapted the tutorial's method of updating field of view to suit my use of scrolling maps. I've implemented some convenience methods on the `GameState` class to make finding entities easier. To get some visual feedback, I've gone ahead and implemented a bit of UI, with a message box appearing at the bottom of the screen. Enemies can now properly be kicked! ![kicked](/screenshots/kick.png)

I also implemented a `drunk_walk` map generator that needs to be tweaked to consistently generate better maps. I did this from memory, so I might need to just find a good drunk-walk example and find out where I went wrong.

Week 3 is, in theory, complete.

## Week 2

More plumbing. With a little bit of refactoring, there is now a module that stores components and a module that will create entities with all the required components. I have decided on using a YAML file (for which I am using the PyYAML library) to store the game data; I find it much easier to quickly edit and read a YAML file than a Python dictionary. I've also decided on a smaller screen size with a large 32x32 font.

Created several modules for drawing and the map. I originally wanted to have a lighter map class that would convert raw tile data - ints, at first - to the proper graphics data when the map was drawn, but I had trouble getting NumPy to play nicely with broadcasting tuple data, so I opted for the method used in the most recent tcod tutorial - with a modification that allows for large, scrolling maps. There is a `Camera` object that keeps track of a viewport, and the `draw_map` function in `ui.py` uses it to draw everything around the player. 

Using `tcod-ecs`'s relations feature, I was able to filter out entities not on the map being drawn. This is a huge step in being able to keep 100% of the game state - including maps - in a single `World`, which will make part 10 much easier. 

I have decided to create my own class which holds the `World` as well as a dictionary of game maps. The `World` has a `mapid` relation that is used to filter out entities on the same map. 

There is also a separate factory function to create a player character.

Finally, the player can no longer go through walls. This completes Week 2.

## Week 1

I've done a bit of plumbing, setting up an `Engine` class to hold the game state and run the game, as well, as a system of `Screen`s that are responsible for handling their own inputs. This will come in handy down the road when I implement things like equipment and shop menus. I've also added `bootstrap.sh` and `bootstrap.bat` to quickly get the virtual environment and dependencies installed. Running the game from a fresh start should be as simple as:

1. `git clone https://github.com/Rakaneth/tcod-tut-2023`
2. `sh bootstrap.sh` (Linux) or  `.\bootstrap.bat` (Windows)
3. `. ./env/bin/activate` (Linux) or `.\env\Scripts\activate` (Windows)
4. `python main.py`

In addition, a minimal Python debug config file for VSCode is included. With Microsoft's Python extension installed, select the Python interpreter in the `./env` folder and then the game can be debugged with `F5`.

Got started early using the brand-spanking-new `tcod-ecs`, which I find less annoying to use than `esper`. There is a bit of a learning curve, but I was able to use it to make a generic entity that could move around and produce the famous `@`.

With that, Week 1 is done. I will try to avoid skipping ahead, but that means I might make a second project alongside this to continue playing with `tcod-ecs`.
