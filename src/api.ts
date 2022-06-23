import { Axios } from "axios";

const axios = new Axios({
  headers: {
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  },
});

export const api = {
  logInGetToken(email: string, password: string) {
    const params = new URLSearchParams();
    // Using FastAPI OAuth2PasswordRequestForm which requires `username` not email
    params.append("username", email);
    params.append("password", password);
    return axios.post(`/notendur/login/access-token`, params);
  },
  getMe() {
    return axios.get(`/notendur/me`);
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
    return axios.post(`/api/follow/cases/${id}`, null);
  },
  unfollowCase(id: string) {
    return axios.delete(`/api/follow/cases/${id}`);
  },
  followEntity(id: string) {
    return axios.post(`/api/follow/entities/${id}`, null);
  },
  unfollowEntity(id: string) {
    return axios.delete(`/api/follow/entities/${id}`);
  },
  followAddress(hnitnum: string) {
    return axios.post(`/api/follow/addresses/${hnitnum}`, null);
  },
  unfollowAddress(hnitnum: string) {
    return axios.delete(`/api/follow/addresses/${hnitnum}`);
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
    return axios.get("/api/_enums");
  },
  getMunicipalities() {
    return axios.get("/api/municipalities");
  },
  getSubscriptions() {
    return axios.get("/api/subscriptions");
  },
  updateSubscription(id: string, data: any) {
    return axios.post(`/api/subscriptions/${id}`, data);
  },
  deleteSubscription(id: string) {
    return axios.delete(`/api/subscriptions/${id}`);
  },
  getPermit(minuteId: string) {
    return axios.get(`/api/minutes/${minuteId}/permit`);
  },
  putPermit(minuteId: string, data: { [key: string]: any }) {
    return axios.put(`/api/minutes/${minuteId}/permit`, data);
  },
};
