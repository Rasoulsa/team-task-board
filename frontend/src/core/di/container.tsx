import { createContext, useContext, useMemo, type ReactNode } from "react";
import { axiosClient } from "../http/axiosClient";
import { HealthRepository } from "../../repositories/HealthRepository";
import { HealthService } from "../../services/HealthService";

export interface Services {
  health: HealthService;
}

const ServicesContext = createContext<Services | null>(null);

export function ServicesProvider({ children }: { children: ReactNode }) {
  const services = useMemo<Services>(() => {
    const healthRepo = new HealthRepository(axiosClient);
    return { health: new HealthService(healthRepo) };
  }, []);
  return <ServicesContext.Provider value={services}>{children}</ServicesContext.Provider>;
}

export function useServices(): Services {
  const ctx = useContext(ServicesContext);
  if (!ctx) throw new Error("useServices must be used within ServicesProvider");
  return ctx;
}
