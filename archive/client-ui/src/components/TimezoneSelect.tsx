import { useState, useRef, useEffect } from "react";
import clsx from "clsx";

// Common timezones with their display names
const TIMEZONES = [
  { value: "America/New_York", label: "Eastern Time (New York)" },
  { value: "America/Chicago", label: "Central Time (Chicago)" },
  { value: "America/Denver", label: "Mountain Time (Denver)" },
  { value: "America/Los_Angeles", label: "Pacific Time (Los Angeles)" },
  { value: "America/Anchorage", label: "Alaska Time (Anchorage)" },
  { value: "Pacific/Honolulu", label: "Hawaii Time (Honolulu)" },
  { value: "Europe/London", label: "Greenwich Mean Time (London)" },
  { value: "Europe/Paris", label: "Central European Time (Paris)" },
  { value: "Europe/Berlin", label: "Central European Time (Berlin)" },
  { value: "Europe/Rome", label: "Central European Time (Rome)" },
  { value: "Europe/Madrid", label: "Central European Time (Madrid)" },
  { value: "Europe/Amsterdam", label: "Central European Time (Amsterdam)" },
  { value: "Europe/Zurich", label: "Central European Time (Zurich)" },
  { value: "Europe/Vienna", label: "Central European Time (Vienna)" },
  { value: "Europe/Stockholm", label: "Central European Time (Stockholm)" },
  { value: "Europe/Oslo", label: "Central European Time (Oslo)" },
  { value: "Europe/Copenhagen", label: "Central European Time (Copenhagen)" },
  { value: "Europe/Helsinki", label: "Eastern European Time (Helsinki)" },
  { value: "Europe/Warsaw", label: "Central European Time (Warsaw)" },
  { value: "Europe/Prague", label: "Central European Time (Prague)" },
  { value: "Europe/Budapest", label: "Central European Time (Budapest)" },
  { value: "Europe/Athens", label: "Eastern European Time (Athens)" },
  { value: "Europe/Istanbul", label: "Turkey Time (Istanbul)" },
  { value: "Europe/Moscow", label: "Moscow Time (Moscow)" },
  { value: "Asia/Dubai", label: "Gulf Standard Time (Dubai)" },
  { value: "Asia/Karachi", label: "Pakistan Standard Time (Karachi)" },
  { value: "Asia/Kolkata", label: "India Standard Time (Mumbai)" },
  { value: "Asia/Dhaka", label: "Bangladesh Standard Time (Dhaka)" },
  { value: "Asia/Bangkok", label: "Indochina Time (Bangkok)" },
  { value: "Asia/Jakarta", label: "Western Indonesia Time (Jakarta)" },
  { value: "Asia/Shanghai", label: "China Standard Time (Shanghai)" },
  { value: "Asia/Hong_Kong", label: "Hong Kong Time (Hong Kong)" },
  { value: "Asia/Tokyo", label: "Japan Standard Time (Tokyo)" },
  { value: "Asia/Seoul", label: "Korea Standard Time (Seoul)" },
  { value: "Australia/Sydney", label: "Australian Eastern Time (Sydney)" },
  {
    value: "Australia/Melbourne",
    label: "Australian Eastern Time (Melbourne)",
  },
  { value: "Australia/Brisbane", label: "Australian Eastern Time (Brisbane)" },
  { value: "Australia/Perth", label: "Australian Western Time (Perth)" },
  { value: "Australia/Adelaide", label: "Australian Central Time (Adelaide)" },
  { value: "Pacific/Auckland", label: "New Zealand Time (Auckland)" },
  { value: "Pacific/Fiji", label: "Fiji Time (Suva)" },
  { value: "America/Sao_Paulo", label: "Brasilia Time (São Paulo)" },
  { value: "America/Buenos_Aires", label: "Argentina Time (Buenos Aires)" },
  { value: "America/Lima", label: "Peru Time (Lima)" },
  { value: "America/Bogota", label: "Colombia Time (Bogotá)" },
  { value: "America/Mexico_City", label: "Central Time (Mexico City)" },
  { value: "America/Toronto", label: "Eastern Time (Toronto)" },
  { value: "America/Vancouver", label: "Pacific Time (Vancouver)" },
  { value: "Africa/Cairo", label: "Eastern European Time (Cairo)" },
  { value: "Africa/Johannesburg", label: "South Africa Time (Johannesburg)" },
  { value: "Africa/Lagos", label: "West Africa Time (Lagos)" },
  { value: "Africa/Nairobi", label: "East Africa Time (Nairobi)" },
];

interface TimezoneSelectProps {
  value: string;
  onChange: (value: string) => void;
  id?: string;
  name?: string;
  className?: string;
}

export function TimezoneSelect({
  value,
  onChange,
  id,
  name,
  className,
}: TimezoneSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredTimezones = TIMEZONES.filter(
    (tz) =>
      tz.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tz.value.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedTimezone = TIMEZONES.find((tz) => tz.value === value);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSearchTerm("");
        setSelectedIndex(-1);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
        e.preventDefault();
        setIsOpen(true);
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredTimezones.length - 1 ? prev + 1 : 0
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : filteredTimezones.length - 1
        );
        break;
      case "Enter":
        e.preventDefault();
        if (selectedIndex >= 0 && filteredTimezones[selectedIndex]) {
          onChange(filteredTimezones[selectedIndex].value);
          setIsOpen(false);
          setSearchTerm("");
          setSelectedIndex(-1);
        }
        break;
      case "Escape":
        setIsOpen(false);
        setSearchTerm("");
        setSelectedIndex(-1);
        break;
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setSelectedIndex(-1);
    if (!isOpen) {
      setIsOpen(true);
    }
  };

  const handleTimezoneClick = (timezone: (typeof TIMEZONES)[0]) => {
    onChange(timezone.value);
    setIsOpen(false);
    setSearchTerm("");
    setSelectedIndex(-1);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <div
        className={clsx(
          "relative cursor-pointer rounded-md border border-slate-300 bg-white px-3 py-2 text-left shadow-sm focus-within:border-primary-500 focus-within:ring-1 focus-within:ring-primary-500",
          className
        )}
        onClick={() => setIsOpen(true)}
      >
        <input
          ref={inputRef}
          type="text"
          id={id}
          name={name}
          value={isOpen ? searchTerm : selectedTimezone?.label || ""}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Search timezone..."
          className="w-full border-none bg-transparent text-sm text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-0"
          readOnly={!isOpen}
        />
        <div className="absolute inset-y-0 right-0 flex items-center pr-2">
          <svg
            className={clsx(
              "h-4 w-4 text-slate-400 transition-transform",
              isOpen && "rotate-180"
            )}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>

      {isOpen && (
        <div className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
          {filteredTimezones.length === 0 ? (
            <div className="px-3 py-2 text-sm text-slate-500">
              No timezones found
            </div>
          ) : (
            filteredTimezones.map((timezone, index) => (
              <div
                key={timezone.value}
                className={clsx(
                  "cursor-pointer px-3 py-2 text-sm",
                  index === selectedIndex
                    ? "bg-primary-100 text-primary-900"
                    : "text-slate-900 hover:bg-slate-100"
                )}
                onClick={() => handleTimezoneClick(timezone)}
              >
                {timezone.label}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
