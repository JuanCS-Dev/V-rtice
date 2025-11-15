import { Toaster as Sonner } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-[rgb(var(--surface-primary))] group-[.toaster]:text-[rgb(var(--text-primary))] group-[.toaster]:border-[rgb(var(--border-primary))] group-[.toaster]:shadow-lg",
          description: "group-[.toast]:text-[rgb(var(--text-secondary))]",
          actionButton:
            "group-[.toast]:bg-primary-600 group-[.toast]:text-white",
          cancelButton:
            "group-[.toast]:bg-[rgb(var(--surface-secondary))] group-[.toast]:text-[rgb(var(--text-secondary))]",
          error:
            "group-[.toaster]:bg-red-50 group-[.toaster]:text-red-900 group-[.toaster]:border-red-200",
          success:
            "group-[.toaster]:bg-primary-50 group-[.toaster]:text-primary-900 group-[.toaster]:border-primary-200",
          warning:
            "group-[.toaster]:bg-amber-50 group-[.toaster]:text-amber-900 group-[.toaster]:border-amber-200",
          info: "group-[.toaster]:bg-blue-50 group-[.toaster]:text-blue-900 group-[.toaster]:border-blue-200",
        },
      }}
      {...props}
    />
  );
};

export { Toaster };
