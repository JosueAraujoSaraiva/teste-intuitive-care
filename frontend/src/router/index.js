import { createRouter, createWebHistory } from "vue-router";
import OperadorasPage from "../pages/OperadorasPage.vue";
import OperadoraDetalhePage from "../pages/OperadoraDetalhePage.vue";

const routes = [
  { path: "/", redirect: "/operadoras" },
  { path: "/operadoras", component: OperadorasPage },
  { path: "/operadoras/:cnpj", component: OperadoraDetalhePage, props: true },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
