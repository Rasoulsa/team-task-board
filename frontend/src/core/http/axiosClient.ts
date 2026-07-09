import axios from "axios";
import { config } from "../config";

export const axiosClient = axios.create({
  baseURL: config.apiUrl,
  headers: { "Content-Type": "application/json" },
});

// token attach interceptor (populated in Day 2)
axiosClient.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("access_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});
