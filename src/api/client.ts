import Axios, { AxiosError, AxiosRequestConfig } from "axios";

export const axios = Axios.create({
  headers: {
    Authorization: `Bearer ${localStorage.getItem("token")}`,
    "Content-Type": "application/json",
  },
  responseType: "json",
});

export const client = async <T>(config: AxiosRequestConfig): Promise<T> => {
  const source = Axios.CancelToken.source();
  const promise = axios({
    ...config,
    cancelToken: source.token,
  }).then(({ data }) => data);

  // @ts-ignore
  promise.cancel = () => {
    source.cancel("Query was cancelled");
  };

  return promise;
};

export function logout() {
  return axios.get("/notendur/logout");
}

export interface ErrorType<Error> extends AxiosError<Error> {}
