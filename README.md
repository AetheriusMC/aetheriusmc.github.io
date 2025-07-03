# AetheriusMC Project

This repository contains the Aetherius Minecraft Server Management Engine and its related components.

## Project Structure

The project is organized to separate the core engine from the server's runtime data, plugins, and components. This makes updating the core engine safer and easier.

- **/Aetherius-Core/**: This is the heart of the project. It contains all the Python source code for the Aetherius management engine. All development on the core functionalities happens here.

- **/server/**: This is the runtime directory for the Minecraft server itself. It contains your `server.jar`, `server.properties`, world data, and other server-specific files. `Aetherius-Core` manages the process running from this directory.

- **/data/**: This directory stores all data generated and used by Aetherius and its plugins/components, such as player databases, statistics, and other persistent information.

- **/plugins/**: Drop your Aetherius plugins (`.py` files or directories) here. The engine will automatically discover and load them from this directory.

- **/components/**: Drop your Aetherius components (heavy-weight extensions) here. The engine will discover and load them from this directory.

**In summary:** You work on the code inside `Aetherius-Core`, and you run the server and store your user-generated content (worlds, plugins, data) in the other top-level directories.
