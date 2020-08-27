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
  followCase(id) {
    return axios.post(`/subscriptions/cases/${id}`, null, authHeaders());
  },
  unfollowCase(id) {
    return axios.delete(`/subscriptions/cases/${id}`, authHeaders());
  },
  followAddress(hnitnum) {
    return axios.post(
      `/subscriptions/addresses/${hnitnum}`,
      null,
      authHeaders()
    );
  },
  unfollowAddress(hnitnum) {
    return axios.delete(`/subscriptions/addresses/${hnitnum}`, authHeaders());
  },
  getEntityAddresses(kennitala) {
    return axios.get(`/entities/${kennitala}/addresses`);
  },
  getSubscriptions() {
    return axios.get("/me/subscriptions", authHeaders());
  },
  updateSubscription(id, active, immediate) {
    return axios.post(
      `/me/subscriptions/${id}`,
      { active: active, immediate: immediate },
      authHeaders()
    );
  },
};
