import { describe, expect, it } from 'vitest';
import { seriesPath } from './Chart';
import type { Frame } from './contracts';

describe('measurement chart gaps and geometry',()=>{
  const sample = (steam: number | null, returned: number | null) => ({readings:{steam_kg_h:steam,return_kg_h:returned}} as Frame);
  it('preserves missing-meter gaps rather than joining through missing data',()=>{
    const values=[sample(100,80),sample(100,null),sample(120,90)];
    expect(seriesPath(values,'return_kg_h',700,231,0,150).match(/M/g)).toHaveLength(2);
    expect(seriesPath(values,'steam_kg_h',700,231,0,150).match(/M/g)).toHaveLength(1);
  });
  it('extends to the right edge when compact layout adds width without changing y coordinates',()=>{
    const values=[sample(100,80),sample(120,90)];
    const full=seriesPath(values,'steam_kg_h',700,231,0,150);
    const compact=seriesPath(values,'steam_kg_h',840,231,0,150);
    expect(full).toContain('L686.00,45.40');
    expect(compact).toContain('L826.00,45.40');
  });
});
