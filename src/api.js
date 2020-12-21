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
    return axios.post(`/api/follow/cases/${id}`, null, authHeaders());
  },
  unfollowCase(id) {
    return axios.delete(`/api/follow/cases/${id}`, authHeaders());
  },
  followEntity(id) {
    return axios.post(`/api/follow/entities/${id}`, null, authHeaders());
  },
  unfollowEntity(id) {
    return axios.delete(`/api/follow/entities/${id}`, authHeaders());
  },
  followAddress(hnitnum) {
    return axios.post(`/api/follow/addresses/${hnitnum}`, null, authHeaders());
  },
  unfollowAddress(hnitnum) {
    return axios.delete(`/api/follow/addresses/${hnitnum}`, authHeaders());
  },
  getEntityAddresses(kennitala) {
    return axios.get(`/api/entities/${kennitala}/addresses`);
  },
  getNearbyAddresses(hnitnum, radius, days) {
    return axios.get(
      `/api/addresses/${hnitnum}/addresses?radius=${radius}&days=${days}`
    );
  },
  getEnums() {
    return axios.get("/api/_enums", authHeaders());
  },
  getMunicipalities() {
    return axios.get("/api/municipalities", authHeaders());
  },
  getSubscriptions() {
    return axios.get("/api/subscriptions", authHeaders());
  },
  updateSubscription(id, data) {
    return axios.post(`/api/subscriptions/${id}`, data, authHeaders());
  },
  deleteSubscription(id) {
    return axios.delete(`/api/subscriptions/${id}`, authHeaders());
  },
  getPermit(minuteId) {
    return axios.get(`/api/minutes/${minuteId}/permit`, authHeaders());
  },
  putPermit(minuteId, data) {
    return axios.put(`/api/minutes/${minuteId}/permit`, data, authHeaders());
  },
};
