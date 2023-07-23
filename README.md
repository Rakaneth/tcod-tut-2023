# Roguelike Dev Tutorial 2023

This is my entry for [r/roguelikedev's](https://reddit.com/r/roguelikedev) annual tutorial event. It is a ~~overdone~~ classic medieval fantasy roguelike set in a world of my own design.

# Progress

* [x] Part 0 - Setting Up
* [x] Part 1 - Drawing the '@' symbol and moving it around
* [x] Part 2 - The generic Entity, the render functions, and the map
* [x] Part 3 - Generating a dungeon
* [x] Part 4 - Field of view
* [x] Part 5 - Placing enemies and kicking them (harmlessly)
* [x] Part 6 - Doing (and taking) some damage
* [x] Part 7 - Creating the interface
* [ ] Part 8 - Items and Inventory
* [ ] Part 9 - Ranged Scrolls and Targeting
* [x] Part 10 - Saving and loading
* [ ] Part 11 - Delving into the Dungeon
* [ ] Part 12 - Increasing Difficulty
* [ ] Part 13 - Gearing up

# Libraries used

[tcod](https://github.com/libtcod/python-tcod), [tcod-ecs](https://github.com/HexDecimal/python-tcod-ecs), pyyaml

# DevLog

## Week 4

So...I'm a whole week ahead now. Bump-attacking is in place, and entities that are slain have their appearances changed, become immobile, and stop blocking. There is currently no death check for the player in place. The player's stats are drawn on the right side of the screen, and things that are hostile to each other deal damage when bumping. I created `combat.py` to group all of the combat-based functions together.

![combat](/screenshots/week4.gif)

### Addendum 2023-7-22

Working on a title screen. Currently, it just shows a list of saved games. With a lot of hacking, save games can be selected from the menu. (Oh, yeah. I implemented a `Menu` class to handle those.) It even has version checks! Currently, an exception is thrown if the game versions do not match.

Maps are now generated based on some map data that describes the layout, items, general difficulty (there I go skipping ahead again), and available monsters types.

I think saving and loading is complete now. The world stores the game save name, which is determined by the starting hero and a timestamp. A `saves` directory is created if one does not exist when the game loads. This is where the game saves are stored. This folder can be deleted wholesale to remove the saved games. I honestly think saving and loading should be done sooner in the project and tested throughout. I am glad to have a version I am happy with.

Also, there are four distinct heroes, with different strengths and weaknesses. All the plumbing done earlier is paying off here; with a few changes to `assets/data/characterdata.yml` and `titlescreen.py`, I can easily add new heroes to the game. Monsters and maps are easier to add.

Now, back to pondering my combat system - and items.

![saving](/screenshots/saving.gif)

### Addendum 2023-7-23

So here I am, up late again, brimming with inspiration.

#### Game Message Improvements

The game messages got a lot of improvements:

* Messages about a specific entity use that entity's render color.
* Messages are now dumped along with save files in a separate `logs/` folder. Considering the size, I will likely use an appending strategy and have the `World` dump the messages at a certain benchmark to keep save file size down.

#### Combat Improvements

There is now a rudimentary on-hit system in place, as well as an effect system. Some attacks or enemies have a chance to cause effects when they hit. The effects are defined in `effects.py` and have a uniform, flexible format. The hope is that some equipment will produce these on-hit effects.

Monster stats are being rebalanced, though I am trying to hold off on a balance pass until I get items in - which I am not far from at this point.

#### UI Improvements

The UI now shows active effects, as well as a map name.

#### Development Improvements

There is now a gamelog that displays game events, out-of-world, as they happen. There is a DEBUG switch in `constants.py` that controls the logging, as I suspect that this will get quite large over a session.

## Week 3

Implemented field of view and basic collision detection. I adapted the tutorial's method of updating field of view to suit my use of scrolling maps. I've implemented some convenience methods on the `GameState` class to make finding entities easier. To get some visual feedback, I've gone ahead and implemented a bit of UI, with a message box appearing at the bottom of the screen. Enemies can now properly be kicked! 

![kicked](/screenshots/kick.gif)

I also implemented a `drunk_walk` map generator that needs to be tweaked to consistently generate better maps. I did this from memory, so I might need to just find a good drunk-walk example and find out where I went wrong.

Week 3 is, in theory, complete.

### Addendum 2023-7-20

I may have been mistaken about that.

A *lot* of cleanup and refactoring happened. There is now a speed system in place. Control is not passed back to the player until they have enough energy to act. Entities act in order of descending speed and gain energy equal to their speed, acting when they have 100. Each game action has an associated cost:

* Moving costs 50
* Bump-attacking costs 50
* More to come

Among the things that got refactored was the `GameState` class. It worked initally until I got some help from @HexDecimal regarding proper use of the World to store arbitrary data. In a night of feverish inspiration (and an unhealthy dose of insomnia), I have removed that class and cleaned up all the functions that relied on the helpers there.

*Now* week 3 is complete. I will likely start week 4 early while I have inspiration.

### Addendum 2023-7-21

I skipped...*way* ahead. It turns out that the main motivation behind me wanting to clean up the gamestate was so that I could do some preliminary saving and loading, and it turns out that my efforts have paid off. Now the world pickles just fine, and I can load the game from a previous save. I tried to do this with the GameState class and it wasn't pickling properly. 

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
