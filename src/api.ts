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
  logInGetToken(email: string, password: string) {
    const params = new URLSearchParams();
    // Using FastAPI OAuth2PasswordRequestForm which requires `username` not email
    params.append("username", email);
    params.append("password", password);
    return axios.post(`/notendur/login/access-token`, params);
  },
  getMe() {
    return axios.get(`/notendur/me`, authHeaders());
  },
  passwordRecovery(email: string) {
    return axios.post(`/notendur/password-recovery/${email}`);
  },
  resetPassword(password: string, token: string) {
    return axios.post(`/notendur/reset-password`, {
      new_password: password,
      token,
    });
  },
  logout() {
    return axios.get("/notendur/logout");
  },
  followCase(id: string) {
    return axios.post(`/api/follow/cases/${id}`, null, authHeaders());
  },
  unfollowCase(id: string) {
    return axios.delete(`/api/follow/cases/${id}`, authHeaders());
  },
  followEntity(id: string) {
    return axios.post(`/api/follow/entities/${id}`, null, authHeaders());
  },
  unfollowEntity(id: string) {
    return axios.delete(`/api/follow/entities/${id}`, authHeaders());
  },
  followAddress(hnitnum: string) {
    return axios.post(`/api/follow/addresses/${hnitnum}`, null, authHeaders());
  },
  unfollowAddress(hnitnum: string) {
    return axios.delete(`/api/follow/addresses/${hnitnum}`, authHeaders());
  },
  getEntityAddresses(kennitala: string) {
    return axios.get(`/api/entities/${kennitala}/addresses`);
  },
  getNearbyAddresses(hnitnum: string, radius: string, days: string) {
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
  updateSubscription(id: string, data: any) {
    return axios.post(`/api/subscriptions/${id}`, data, authHeaders());
  },
  deleteSubscription(id: string) {
    return axios.delete(`/api/subscriptions/${id}`, authHeaders());
  },
  getPermit(minuteId: string) {
    return axios.get(`/api/minutes/${minuteId}/permit`, authHeaders());
  },
  putPermit(minuteId: string, data: { [key: string]: any }) {
    return axios.put(`/api/minutes/${minuteId}/permit`, data, authHeaders());
  },
};
