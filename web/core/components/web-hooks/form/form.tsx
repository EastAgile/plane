"use client";

import React, { FC, useEffect, useState } from "react";
import { observer } from "mobx-react";
import { Controller, useForm } from "react-hook-form";
import { IWebhook, TWebhookEventTypes, TWebhookProjectType } from "@plane/types";
// hooks
import { Button } from "@plane/ui";
import {
  WebhookIndividualEventOptions,
  WebhookInput,
  WebhookOptions,
  WebhookProjectSelection,
  WebhookSecretKey,
  WebhookToggle,
} from "@/components/web-hooks";
import { useWebhook, useProject } from "@/hooks/store";
// components
// ui
// types

type Props = {
  data?: Partial<IWebhook>;
  onSubmit: (data: IWebhook, webhookEventType: TWebhookEventTypes) => Promise<void>;
  handleClose?: () => void;
};

const initialWebhookPayload: Partial<IWebhook> = {
  cycle: true,
  issue: true,
  issue_comment: true,
  module: true,
  project: true,
  url: "",
};

export const WebhookForm: FC<Props> = observer((props) => {
  const { data, onSubmit, handleClose } = props;
  // states
  const [webhookEventType, setWebhookEventType] = useState<TWebhookEventTypes>("all");
  const [projectType, setProjectType] = useState<TWebhookProjectType>("all"); // TODO: update `"all" | "individual"` into a type
  const [selectedProjects, setSelectedProjects] = useState<string[]>([]);

  // store hooks
  const { webhookSecretKey } = useWebhook();
  const { workspaceProjectIds, projectMap, loader: projectsLoading } = useProject();

  // transform project data from store
  const projectsList = workspaceProjectIds
    ? workspaceProjectIds.map((projectId) => ({
        id: projectId,
        name: projectMap[projectId]?.name || "",
      }))
    : [];

  // use form
  const {
    handleSubmit,
    control,
    formState: { isSubmitting, errors },
  } = useForm<IWebhook>({
    defaultValues: { ...initialWebhookPayload, ...data },
  });

  const handleFormSubmit = async (formData: IWebhook) => {
    // Include project selection data in the submission
    const submissionData = {
      ...formData,
      project_type: projectType,
      selected_projects: selectedProjects,
    };
    await onSubmit(submissionData, webhookEventType);
  };

  useEffect(() => {
    if (!data) return;

    if (data.project && data.cycle && data.module && data.issue && data.issue_comment) {
      setWebhookEventType("all");
    } else {
      setWebhookEventType("individual");
    }

    // Set project type and selected projects if they exist in data
    if (data.project_type) {
      setProjectType(data.project_type as "all" | "individual");
      if (data.selected_projects) {
        setSelectedProjects(data.selected_projects as string[]);
      }
    }
  }, [data]);

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)}>
      <div className="space-y-5">
        <div className="text-xl font-medium text-custom-text-200">
          {data ? "Webhook details" : "Create webhook"}
        </div>
        <div className="space-y-4">
          <div className="space-y-1">
            <Controller
              control={control}
              name="url"
              rules={{
                required: "URL is required",
              }}
              render={({ field: { onChange, value } }) => (
                <WebhookInput value={value} onChange={onChange} hasError={Boolean(errors.url)} />
              )}
            />
            {errors.url && <div className="text-xs text-red-500">{errors.url.message}</div>}
          </div>

          {data && <WebhookToggle control={control} />}

          <WebhookOptions value={webhookEventType} onChange={(val) => setWebhookEventType(val)} />

          {webhookEventType === "individual" && <WebhookIndividualEventOptions control={control} />}

          {projectsLoading ? (
            <div className="text-sm text-custom-text-200">Loading projects...</div>
          ) : (
            <WebhookProjectSelection
              projectValue={projectType}
              selectedProjects={selectedProjects}
              projects={projectsList}
              onProjectTypeChange={setProjectType}
              onProjectsChange={setSelectedProjects}
            />
          )}
        </div>
      </div>

      {data ? (
        <div className="pt-4 space-y-5">
          <WebhookSecretKey data={data} />
          <Button type="submit" loading={isSubmitting}>
            {isSubmitting ? "Updating" : "Update"}
          </Button>
        </div>
      ) : (
        <div className="px-5 py-4 flex items-center justify-end gap-2 border-t-[0.5px] border-custom-border-200">
          <Button variant="neutral-primary" size="sm" onClick={handleClose}>
            Cancel
          </Button>
          {!webhookSecretKey && (
            <Button type="submit" variant="primary" size="sm" loading={isSubmitting}>
              {isSubmitting ? "Creating" : "Create"}
            </Button>
          )}
        </div>
      )}
    </form>
  );
});