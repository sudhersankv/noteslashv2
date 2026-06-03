import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-xl border border-neutral-200 bg-white p-5 shadow-sm", className)}
      {...props}
    />
  );
}
