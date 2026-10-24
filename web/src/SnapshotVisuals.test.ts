import { expect, it } from 'vitest';
import type { Event } from './contracts';
import { eventBins } from './SnapshotVisuals';

it('interruption counts exclude mode/warmup/restoration and future records',()=>{
  const event=(timestamp:string,quality_action:string)=>({timestamp,quality_action,category:'quality'} as Event);
  const events=[event('2026-01-01T11:57:00Z','MODE_STABILIZATION'),event('2026-01-01T11:58:00Z','GATEWAY_OFFLINE'),event('2026-01-01T11:59:00Z','SCORE_ALLOWED'),event('2026-01-01T12:00:00Z','VERIFY_RETURN_METER'),event('2026-01-01T12:01:00Z','GATEWAY_OFFLINE')];
  const bins=eventBins(events,'quality','2026-01-01T12:00:00Z');
  expect(bins).toHaveLength(13);expect(bins.reduce((a,b)=>a+b,0)).toBe(2);
  expect(eventBins([],'return','2026-01-01T12:00:00Z')).toEqual(Array(13).fill(0));
});
