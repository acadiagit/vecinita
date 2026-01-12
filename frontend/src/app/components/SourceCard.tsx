import React from 'react';
import { ExternalLink } from 'lucide-react';

export interface Source {
  title: string;
  url: string;
  snippet?: string;
}

interface SourceCardProps {
  source: Source;
  index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-2 sm:p-3 rounded-lg border border-border bg-card hover:bg-accent transition-colors group"
      aria-label={`Source ${index + 1}: ${source.title}`}
    >
      <div className="flex items-start gap-1.5 sm:gap-2">
        <span className="text-primary shrink-0 mt-0.5 text-xs sm:text-sm" aria-hidden="true">
          [{index + 1}]
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-1.5 sm:gap-2">
            <h4 className="text-xs sm:text-sm text-foreground group-hover:text-primary transition-colors line-clamp-2">
              {source.title}
            </h4>
            <ExternalLink className="w-3 h-3 sm:w-4 sm:h-4 text-muted-foreground shrink-0 mt-0.5" aria-hidden="true" />
          </div>
          {source.snippet && (
            <p className="text-[10px] sm:text-xs text-muted-foreground mt-1 line-clamp-2">
              {source.snippet}
            </p>
          )}
        </div>
      </div>
    </a>
  );
}