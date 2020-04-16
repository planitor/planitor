import axios from "axios";

function authHeaders(token) {
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
  getMe(token) {
    return axios.get(`/notendur/users/me`, authHeaders(token));
  },
  updateMe(token, data) {
    return axios.put(`/notendur/users/me`, data, authHeaders(token));
  },
  getUsers(token) {
    return axios.get(`/notendur/users/`, authHeaders(token));
  },
  updateUser(token, userId, data) {
    return axios.put(`/notendur/users/${userId}`, data, authHeaders(token));
  },
  createUser(token, data) {
    return axios.post(`/notendur/users/`, data, authHeaders(token));
  },
  passwordRecovery(email) {
    return axios.post(`/notendur/password-recovery/${email}`);
  },
  resetPassword(password, token) {
    return axios.post(`/notendur/reset-password/`, {
      new_password: password,
      token,
    });
  },
};
