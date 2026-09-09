import { describe, expect, it } from "vitest";

import { isAcceptedImportFile } from "./importHelpers";

describe("importHelpers", () => {
  it("accepte JSONL, CSV et Parquet", () => {
    expect(isAcceptedImportFile(new File(["a"], "traces.jsonl"))).toBe(true);
    expect(isAcceptedImportFile(new File(["a"], "data.csv"))).toBe(true);
    expect(isAcceptedImportFile(new File(["a"], "data.parquet"))).toBe(true);
  });

  it("refuse les autres extensions", () => {
    expect(isAcceptedImportFile(new File(["a"], "notes.txt"))).toBe(false);
    expect(isAcceptedImportFile(new File(["a"], "archive.zip"))).toBe(false);
  });
});
