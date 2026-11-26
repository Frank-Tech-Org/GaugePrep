import type * as React from 'react';
/** The one action a view is for (primary, at most once per view), or a supporting action. */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> { variant?: 'primary' | 'secondary' | 'ghost'; size?: 'md' | 'sm' }
export declare function Button(props: ButtonProps): React.ReactElement;
/** A level in the exam's own scale (CEFR A1-C2, NCLC 1-12, IELTS band...). */
export interface LevelBadgeProps { level: string; label?: string; tone?: 'neutral' | 'reading' | 'target' }
export declare function LevelBadge(props: LevelBadgeProps): React.ReactElement;
/** The brand gauge as UI: one page per level, the reading in amber, levels above it unreached. */
export interface ScoreGaugeProps { levels?: string[]; reading: number; value?: string; label?: string; caption?: string }
export declare function ScoreGauge(props: ScoreGaugeProps): React.ReactElement;
declare global { interface Window { GaugePrep: { Button: typeof Button; LevelBadge: typeof LevelBadge; ScoreGauge: typeof ScoreGauge } } }
