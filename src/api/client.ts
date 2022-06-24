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
  console.log("AXIOS!", config);
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

export function logInGetToken(email, password) {
  const params = new URLSearchParams();
  // Using FastAPI OAuth2PasswordRequestForm which requires `username` not email
  params.append("username", email);
  params.append("password", password);
  return axios.post(`/notendur/login/access-token`, params);
}

export function getMe() {
  return axios.get(`/notendur/me`);
}

export function passwordRecovery(email) {
  return axios.post(`/notendur/password-recovery/${email}`);
}

export function resetPassword(password, token) {
  return axios.post(`/notendur/reset-password`, {
    new_password: password,
    token,
  });
}

export function logout() {
  return axios.get("/notendur/logout");
}

export interface ErrorType<Error> extends AxiosError<Error> {}
