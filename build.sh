#!/bin/sh

nixos-rebuild build --flake /home/richie/projects/dotfiles#bob
nixos-rebuild build --flake /home/richie/projects/dotfiles#jeeves
nixos-rebuild build --flake /home/richie/projects/dotfiles#muninn
nixos-rebuild build --flake /home/richie/projects/dotfiles#rhapsody-in-green