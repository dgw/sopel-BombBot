# willie-BombBot
Customized version of a custom version of a bomb module for willie

## Dependencies
* `__future__`: `division` and `unicode_literals`
* `random` (standard library)
* `threading` (standard library)
* `time` (standard library)

## Commands
* Gameplay:
  * `.bomb <nick>`: Plant a bomb on `nick` that they will have to defuse by guessing
                  which wire to cut.
  * `.cutwire <color>`: Cut one of the colored wires listed in the bomb-planted message.
  * `.bombcancel <nick>`: Cancel the bomb planted on `nick` (can be used by bomber or an admin).
* Stats:
  * `.bombs [nick]`: Get stats on your own (or `nick`'s) bomb-defusing prowess.
  * `.bombstatreset <nick>`: Bot admins only; resets the given user's stats to zero.
* User Controls:
  * `.bombon`/`.bomboff`: Lets users enable/disable being bombed at will. Admins can specify a nick.
* Channel Controls
  * `.bombson`/`.bombsoff`: Lets channel admins enable/disable bombing in the current channel.
  * `.bombkickon`/`.bombkickoff`: Lets channel admins enable/disable kicking for bombs in the current channel.

