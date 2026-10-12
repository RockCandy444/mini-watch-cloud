import { request } from "./client";
export const listEvents = (filters = {}) =>
  request(`/events?${new URLSearchParams(filters)}`);
