import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
};

export function Button({
  className,
  variant = "primary",
  size = "md",
  ...props
}: Props) {
  const base =
    "inline-flex items-center justify-center rounded-lg font-medium transition disabled:opacity-50 disabled:pointer-events-none";
  const variants = {
    primary: "bg-neutral-900 text-white hover:bg-neutral-800",
    secondary: "border border-neutral-300 bg-white hover:bg-neutral-50",
    ghost: "hover:bg-neutral-100",
  };
  const sizes = { sm: "px-3 py-1.5 text-sm", md: "px-4 py-2 text-sm", lg: "px-6 py-3" };
  return (
    <button
      className={cn(base, variants[variant], sizes[size], className)}
      {...props}
    />
  );
}
