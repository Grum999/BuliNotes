# Buli Notes :: Release 1.0.0 [2022-XX-XX]


# Bug

## Fix ***Crash when multiples windows are opened***

[Bug fix #1](https://github.com/Grum999/BuliNotes/issues/1)

When A new window is created, BuliNotes generates a python exception.

This has been fixed.


## Fix ***unhashable type: 'Resource'***

When no brush can be found, the fallback is to get the first available brush found in brushes preset.
A technical bug was returning the brush resource instead of expected name of resource.
