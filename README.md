# Drone-Web-App

This repository provides a web application to manage and control drones equipped with Raspberry Pi via a local network. It features the ability to scan for available drones, select drop coordinates on Google Maps, and customize mission parameters by editing waypoints. The backend uses Flask for handling API requests and PyMavlink to send commands and load mission waypoints to the drone.

## Table of Contents
- [Features](#Features)
- [Assumptions](#assumptions)
- [Current Mission Waypoints Format](#current-mission-waypoints-format)
- [Technology Stack](#technology-stack)
- [Usage](#usage)
  - [Backend](#backend)
  - [Frontend](#frontend)
- [Mission Parameters Customization](#mission-parameters-customization)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)


## Features

- **Drone Discovery**: Scans the local network to find drones that are available and connected.
- **Drop Coordinates Selection**: Users can pick the drop coordinates using a Google Maps component and send them to the drone.
- **Waypoint Customization**: Users can customize the drone's mission parameters by editing waypoints manually.
- **Good Error Handling**: The app is built with robust error-handling mechanisms to ensure smooth operation and provide meaningful feedback.

## Assumptions

- Each drone has a Raspberry Pi onboard, running a service that exposes a `/drop_coordinates` API endpoint. This endpoint is used to send the target coordinates to the drone.
  
## Current Mission Waypoints Format

The mission waypoints follow the `QGC WPL 110` format, which looks like this:

```
QGC WPL 110
0	1	0	16	0	0	0	0	-35.3633516	149.1652413	587.150000	1
1	0	3	22	0.00000000	0.00000000	0.00000000	0.00000000	0.00000000	0.00000000	10.000000	1
2	0	3	16	0.00000000	0.00000000	0.00000000	0.00000000	-35.36199670	149.16602790	10.000000	1
3	0	3	19	10.00000000	0.00000000	0.00000000	0.00000000	0.00000000	0.00000000	1.000000	1
4	0	3	20	0.00000000	0.00000000	0.00000000	0.00000000	0.00000000	0.000000	1
```

This format can be edited to define the drone's mission, including specific commands, latitudes, longitudes, and altitudes for each waypoint.

## Technology Stack

- **Frontend**: Next.js
  - Used for building the user interface, including map integration for selecting drop coordinates.

- **Backend**: Flask
  - Manages API requests and drone communication.

- **Drone Control**: PyMavlink
  - Sends commands and mission waypoints to drones using the MAVLink protocol.

- **Mapping**: Google Maps API
  - Provides the map interface for selecting and viewing drop coordinates.

## Usage

**Clone the repository**:
   ```bash
   git clone https://github.com/Pranav904/Drone-Web-App.git
   cd Drone-Web-App
   ```
#### Backend
1. **Install Dependencies**:
   The application requires Python dependencies, including Flask and PyMavlink. Install them using `pip`:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   Start the Flask server using the following command (single drone):
   ```bash
   python drone_delivery.py
   ```
   
   Start the Flask server using the following command (multiple drones):
   ```bash
   python drone_delivery_dx.py
   ```
   where `x` is the drone number.

#### Frontend
   
1. **Navigate to Frontend**:
   ```bash
   cd aerodrop
   ```

2. **Install NPM Modules:**
   The application also requires Node.js modules for the front-end. Install them using npm:
   ```bash
   npm install
   ```

3. **Configure Google Maps API Key**:
   Create a `.env.local` file in the `aerodrop` directory and add your Google Maps API key from GCP:
   ```bash
   NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-api-key-here
   ```

4. **Launch the Web Server**:
   Launch the Next.js Web Server
   ```bash
   npm run dev
   ```
   
5. **Access the Web App**:
   Once the server is running, you can access the web interface via your browser at:
   ```
   http://localhost:3000
   ```

## Note !

- **Google Maps API Key**: Make sure to create a `.env.local` file inside the `aerodrop` directory and include your Google Maps API key (`NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`). This key is required for the map functionality to work correctly in the frontend.

### Where to Add the `.env.local` File:
- Go to the `aerodrop` directory.
- Create a file named `.env.local`.
- Inside the file, add the following line:
  ```bash
  NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-api-key-here
  ```

This `.env.local` file will ensure that the Google Maps API key is available to the Next.js frontend.

## Mission Parameters Customization

The waypoints can be manually edited in the application to customize mission parameters. Each waypoint defines:

- Latitude and longitude for the drone to travel.
- Altitude and mission-specific commands.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue for any bugs or feature requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

## Contact

For any queries, feel free to reach out to the repository owner via GitHub or submit an issue on the repository.
