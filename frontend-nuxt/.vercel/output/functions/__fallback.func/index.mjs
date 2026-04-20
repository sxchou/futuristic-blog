import process from 'node:process';globalThis._importMeta_={url:import.meta.url,env:process.env};import { p as parseQuery, g as getRouteRulesForPath, w as withQuery, t as toNodeListener, u as useNitroApp } from './chunks/_/nitro.mjs';
import 'node:http';
import 'node:https';
import 'node:events';
import 'node:buffer';
import 'node:fs';
import 'node:path';
import 'node:crypto';

const ISR_URL_PARAM = "__isr_route";

const nitroApp = useNitroApp();
const handler = toNodeListener(nitroApp.h3App);
const listener = function(req, res) {
  const isrRoute = req.headers["x-now-route-matches"];
  if (isrRoute) {
    const { [ISR_URL_PARAM]: url } = parseQuery(isrRoute);
    if (url && typeof url === "string") {
      const routeRules = getRouteRulesForPath(url);
      if (routeRules.isr) {
        req.url = url;
      }
    }
  } else {
    const queryIndex = req.url.indexOf("?");
    const urlQueryIndex = queryIndex === -1 ? -1 : req.url.indexOf(`${ISR_URL_PARAM}=`, queryIndex);
    if (urlQueryIndex !== -1) {
      const { [ISR_URL_PARAM]: url, ...params } = parseQuery(
        req.url.slice(queryIndex)
      );
      if (url && typeof url === "string") {
        const routeRules = getRouteRulesForPath(url);
        if (routeRules.isr) {
          req.url = withQuery(url, params);
        }
      }
    }
  }
  return handler(req, res);
};

export { listener as default };
//# sourceMappingURL=index.mjs.map
