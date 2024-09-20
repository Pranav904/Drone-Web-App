// MissionMap.js
import React from "react";
import { GoogleMap, LoadScript, Marker } from "@react-google-maps/api";

const mapContainerStyle = {
  width: "98%",
  height: "100%",
};

const center = {
  lat: 12.841,
  lng: 80.154,
};

const MissionMap = ({ markerPosition, onMapClick }) => {
  return (
    <div className="map-container">
      <LoadScript
        googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY}
      >
        <GoogleMap
          mapContainerStyle={mapContainerStyle}
          center={center}
          zoom={18}
          onClick={onMapClick}
        >
          {markerPosition && <Marker position={markerPosition} />}
        </GoogleMap>
      </LoadScript>
    </div>
  );
};

export default MissionMap;