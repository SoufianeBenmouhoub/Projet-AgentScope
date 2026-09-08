/**
 * Configuration commune des tests du front.
 *
 * Sans ce nettoyage, le DOM d'un test reste monté pendant le suivant : les requêtes
 * `getByText` trouvent alors plusieurs éléments et échouent avec un message trompeur qui
 * désigne le mauvais coupable. Testing Library ne l'enregistre automatiquement que lorsque
 * les globales de Vitest sont activées, ce qui n'est pas le cas ici.
 */

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});
