//src/components/PartnerSelector.jsx
import React from "react";
import {
  TruckIcon,
  PackageIcon,
  GlobeIcon,
  ArchiveIcon,
  RepeatIcon,
  BoxIcon,
} from "lucide-react";

const options = [
  { key: "brenger",     label: "Brenger",       icon: <TruckIcon className="h-5 w-5" /> },
  { key: "wuunder",     label: "Wuunder",       icon: <PackageIcon className="h-5 w-5" /> },
  { key: "libero",      label: "Libero",        icon: <GlobeIcon className="h-5 w-5" /> },
  { key: "swdevries",   label: "Sw De Vries",   icon: <ArchiveIcon className="h-5 w-5" /> },
  { key: "transpoksi",  label: "Transpoksi",    icon: <RepeatIcon className="h-5 w-5" /> },
  { key: "magic_movers",label: "Magic Movers",  icon: <BoxIcon className="h-5 w-5" /> },
];

export default function PartnerSelector({ partner, setPartner }) {
  return (
    <div className="inline-flex bg-muted rounded-full p-1 space-x-1 sidebar-transition">
      {options.map((opt) => {
        const active = partner === opt.key;
        return (
          <button
            key={opt.key}
            onClick={() => setPartner(opt.key)}
            className={`
              flex items-center space-x-2 px-4 py-2 rounded-full
              text-sm font-medium transition-colors duration-200
              ${active
                ? "bg-accent text-white shadow"
                : "text-primary hover:bg-white"}
            `}
          >
            {React.cloneElement(opt.icon, {
              className: active ? "h-5 w-5 text-white" : "h-5 w-5 text-primary",
            })}
            <span>{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}
