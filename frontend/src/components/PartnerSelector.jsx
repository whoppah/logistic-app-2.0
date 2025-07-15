// frontend/src/components/PartnerSelector.jsx
import React from "react";
import {
  TruckIcon,
  PackageIcon,
  GlobeIcon,
  ArchiveIcon,
  RepeatIcon,
  BoxIcon,
  Activity,
} from "lucide-react";

const options = [
  { key: "brenger",      label: "Brenger",       icon: <TruckIcon /> },
  { key: "libero",       label: "Libero",        icon: <GlobeIcon /> },
  { key: "swdevries",    label: "SwDeVries",   icon: <ArchiveIcon /> },
  { key: "wuunder",      label: "Wuunder",       icon: <PackageIcon /> },
  { key: "magic_movers", label: "MagicMovers",  icon: <BoxIcon /> },
  { key: "transpoksi",   label: "Transpoksi",    icon: <RepeatIcon /> },
  { key: "tadde",        label: "Tadde",         icon: <Activity /> },
];

export default function PartnerSelector({ partner, setPartner }) {
  return (
    <div
      className="
        flex flex-nowrap overflow-x-auto         /* no wrap, scroll on overflow */
        bg-muted rounded-full p-1 space-x-1
        sidebar-transition
      "
    >
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
                : "text-primary hover:bg-white"
              }
            `}
          >
            {React.cloneElement(opt.icon, {
              className: `h-5 w-5 ${active ? "text-white" : "text-primary"}`,
            })}
            <span>{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}
