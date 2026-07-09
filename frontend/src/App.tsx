import { useEffect, useState } from "react";
import { useServices } from "./core/di/container";

export default function App() {
  const { health } = useServices();
  const [status, setStatus] = useState("checking...");

  useEffect(() => {
    health.check().then(setStatus).catch(() => setStatus("backend unreachable"));
  }, [health]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="p-8 bg-white rounded-xl shadow">
        <h1 className="text-2xl font-bold">Team Task Board</h1>
        <p className="mt-2 text-gray-600">Backend: <span className="font-mono">{status}</span></p>
      </div>
    </div>
  );
}
