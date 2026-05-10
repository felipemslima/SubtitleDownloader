export type ApiEnvelope<T> = {
  ok: boolean;
  data: T;
  error?: string;
};
