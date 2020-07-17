import axios from "axios";

function authHeaders() {
  const token = localStorage.getItem("token");
  return {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  };
}

export const api = {
  logInGetToken(email, password) {
    const params = new URLSearchParams();
    // Using FastAPI OAuth2PasswordRequestForm which requires `username` not email
    params.append("username", email);
    params.append("password", password);
    return axios.post(`/notendur/login/access-token`, params);
  },
  getMe() {
    return axios.get(`/notendur/me`, authHeaders());
  },
  passwordRecovery(email) {
    return axios.post(`/notendur/password-recovery/${email}`);
  },
  resetPassword(password, token) {
    return axios.post(`/notendur/reset-password`, {
      new_password: password,
      token,
    });
  },
  logout() {
    return axios.get("/notendur/logout");
  },
};
