// web/core/components/web-hooks/form/project-selection.tsx

import { FC, useState } from "react";
import { Check, Search } from "lucide-react";
import { Combobox } from "@headlessui/react";

import { TWebhookProjectType } from "@plane/types";

const PROJECT_SELECTION_TYPES = [
  {
    key: "all",
    label: "All Projects",
  },
  {
    key: "individual",
    label: "Select individual projects",
  },
];

type Props = {
  projectValue: TWebhookProjectType;
  selectedProjects: string[];
  projects: { id: string; name: string }[];
  onProjectTypeChange: (value: TWebhookProjectType) => void;
  onProjectsChange: (projects: string[]) => void;
};

export const WebhookProjectSelection: FC<Props> = ({
  projectValue,
  selectedProjects,
  projects,
  onProjectTypeChange,
  onProjectsChange,
}) => {
  const [query, setQuery] = useState("");

  const filteredProjects = query === ""
    ? projects
    : projects.filter((project) => project.name.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="space-y-3">
      <h6 className="text-sm font-medium">Select projects for webhook</h6>
      <div className="space-y-3">
        {PROJECT_SELECTION_TYPES.map((option) => (
          <div key={option.key} className="flex items-center gap-2">
            <input
              id={`project-${option.key}`}
              type="radio"
              value={option.key}
              checked={projectValue === option.key}
              onChange={() => onProjectTypeChange(option.key as "all" | "individual")}
            />
            <label className="text-sm" htmlFor={`project-${option.key}`}>
              {option.label}
            </label>
          </div>
        ))}
      </div>

      {projectValue === "individual" && (
        <div className="mt-4">
          <Combobox value={selectedProjects} onChange={onProjectsChange} multiple>
            <div className="relative">
              <div className="flex flex-wrap gap-2 mb-2">
                {selectedProjects.map((projectId) => {
                  const project = projects.find((p) => p.id === projectId);
                  if (!project) return null;
                  return (
                    <div
                      key={projectId}
                      className="flex items-center gap-1 truncate rounded-full border border-custom-border-100 px-2 py-0.5 text-xs"
                    >
                      <span>{project.name}</span>
                      <button
                        className="text-custom-text-300 hover:text-custom-text-100"
                        onClick={() => onProjectsChange(selectedProjects.filter((id) => id !== projectId))}
                      >
                        ×
                      </button>
                    </div>
                  );
                })}
              </div>

              <div className="relative">
                <div className="flex w-full items-center justify-start rounded border border-custom-border-200 bg-custom-background-90 px-2">
                  <Search className="h-3.5 w-3.5 text-custom-text-300" />
                  <Combobox.Input
                    className="w-full bg-transparent px-2 py-1 text-xs text-custom-text-200 placeholder:text-custom-text-400 focus:outline-none"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Start typing to filter projects..."
                  />
                </div>

                <Combobox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded border border-custom-border-300 bg-custom-background-100 py-1 text-sm shadow-lg">
                  {filteredProjects.map((project) => (
                    <Combobox.Option
                      key={project.id}
                      value={project.id}
                      className={({ active, selected }) =>
                        `cursor-pointer select-none px-2 py-1.5 ${
                          active ? "bg-custom-background-80" : ""
                        } ${selected ? "text-custom-text-100" : "text-custom-text-200"}`
                      }
                    >
                      {({ selected }) => (
                        <div className="flex items-center justify-between">
                          <span>{project.name}</span>
                          {selected && <Check className="h-3.5 w-3.5" />}
                        </div>
                      )}
                    </Combobox.Option>
                  ))}
                </Combobox.Options>
              </div>
            </div>
          </Combobox>
        </div>
      )}
    </div>
  );
};