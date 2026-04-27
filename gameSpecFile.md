## Game spec file
**Working titel:** Underwater side scrolling spearfish shooter

Titel in game: Spearfisherz

Library: Pygame
Dimensions: 2D
Style: Pixel art.
Gameplay: **Side-Scrolling Shooter**

### Main Game:
The player controls a spearfisher which starts on the left side of the screen. The surface is almost at the top of the screen, i.e. nothing happening above the surface.
Underwater there is a simple parkour/ course of rocks where the player ha to manouver the spearfisher through. Once in a while a fish spawns from the right which the player can shoot and earns points. The player has three lives. When hitting a rock he loses one live. When loosing the third live the game is over.

### Player/ Figure
A spearfisher with a speargun which is the same size/ length of the spearfisher.
If the spearfisher shoots his speargun, a shaft, which is bound to the gun via a string or rope, fires about four of the length of the spearfisher and then return into the speargun. Ideally also the fins would move a bit up and down. The spearfisher is holding his breath which means there should be a breath bar in the top right showing the remaining breath of the spearfisher. On the surface he can slowly refill this bar. The spearfisher should be able to hold his breath 10 seconds, after that every 1 second one live should be removed.
The lives should be dsiplayed three hearts next to each other.

### Fish
When the spearfisher hits a fish with the shaft, it should be stabbed by the shaft and return with the shaft to the speargun and then disappear.
There should be three kind of fish:
1. A smaller one which should look like the mediterranean parrotfish. This one provides 1 point when shooted. The behaviour of this fish is that it just slowly swims around and is not scared by the spearfisher.
2. A bigger one which sound look like Sea bream. This one provides 10 points when shooted. The behavior of this fish is that if the spearfisher moves a lot while being close the fish is scared and swims away. If the spearfisher approaches straight, thus without movemet it is not scared and does not swim away.
3. A medium sized one which should look like a brown grouper. This one should substract 20 points from the score hwen shooted. The behaviour of this fish is that it is slighty attracted by the spearfisher and swims slowly towards him.

### The rocks
The rocks should lay on the ground of the sea bottom, some of them reaching higher, some lower! They can even reach almost to the surface where the spearfisher has to swim completly to the surface.


### Audio
The main theme should be a nice retro underwater world sound/ song.
When the spearfisher hits a rock there should be a "Ouch!" Sound.
When the spearfisher fires his gun there should be a firing sound.
When the spearfisher catches a fish, there should be a scoring sound.
When the spearfisher runs out of breath, there should be a adequate sound.