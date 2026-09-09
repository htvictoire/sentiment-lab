import type { ReactNode } from "react";
import { TabsList } from "@/components/tabs";

type ScrollableTabsListProps = {
  readonly children: ReactNode;
};

export function ScrollableTabsList({ children }: ScrollableTabsListProps) {
  return (
    <div className="-mx-1 overflow-x-auto px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <TabsList className="w-max min-w-full group-data-horizontal/tabs:h-11" variant="line">
        {children}
      </TabsList>
    </div>
  );
}
