# sopel-bombbot

A bomb-defusing game for Sopel IRC bots.

Behavioral clone of someone else's bot, originally based on John Lage's
EFLv2-licensed [`bomb.py`][upstream-repo] module.

[upstream-repo]: https://github.com/johnlage/BombBot

## Installing

Releases are hosted on PyPI, so after installing Sopel, all you need is `pip`:

```shell
$ pip install sopel-bombbot
```

## Configuring

The easiest way to configure `sopel-bombbot` is via Sopel's configuration
wizard—simply run `sopel-plugins configure bombbot` and enter the values for
which it prompts you.

Available settings are:

* `fuse` - How long (in seconds) between when the bomb is planted and when it
  goes off.
* `cooldown` - How long (in seconds) the same user must wait before planting
  another bomb.

```ini
[bombbot]
# the default values are:
fuse = 120
cooldown = 600
```

## Using

* **Gameplay:**
  * `.bomb <nick>`: Plant a bomb on `nick` that they will have to defuse by
    guessing which wire to cut.
  * `.cutwire <color>`: Cut one of the colored wires listed in the "bomb
    planted" message.
  * `.bombcancel <nick>`: Cancel the bomb planted on `nick` (can be used by the
    bomber or an admin).
* **Stats:**
  * `.bombs [nick]`: Get stats on your own (or `nick`'s) bomb-defusing prowess.
  * `.bombstatreset <nick>`: Bot admins only; resets the given user's stats to
    zero.
* **User Controls:**
  * `.bombon`/`.bomboff`: Lets users enable/disable being bombed at will. Admins
    can specify a nick.
* **Channel Controls:**
  * `.bombing [on|off]`: Lets channel admins enable/disable bombing in the
    current channel.
  * `.bombkicks [on|off]`: Lets channel admins enable/disable kicking for bombs
    in the current channel.

