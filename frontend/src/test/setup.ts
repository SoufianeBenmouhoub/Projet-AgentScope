/**
 * Configuration commune des tests du front.
 *
 * Sans ce nettoyage, le DOM d'un test reste monté pendant le suivant : les requêtes
 * `getByText` trouvent alors plusieurs éléments et échouent avec un message trompeur.
 */

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});
