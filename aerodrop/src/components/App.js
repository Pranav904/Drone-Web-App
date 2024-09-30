"use client";

import React from "react";
import MissionForm from "./MissionForm";
import { BackgroundBeams } from "./ui/background-beams";
import "./App.css";

function App() {
  return (
    <div className="App bg-neutral-950 h-screen w-full">
      <div className="relative z-10">
        <MissionForm />
      </div>
      <BackgroundBeams />
    </div>
  );
}

export default App;
