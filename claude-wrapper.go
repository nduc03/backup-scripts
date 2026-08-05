package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
)

const disallowedTools = "NotebookEdit,WebSearch,WebFetch,CronCreate,CronDelete,CronList,PushNotification,RemoteTrigger,ReportFindings,ScheduleWakeup,EnterWorktree,ExitWorktree,Artifact,ShareOnboardingGuide,SendMessage,SendUserFile,Workflow,TaskOutput,ExitPlanMode"

func main() {
	var target string
	var args []string

	if len(os.Args) >= 2 &&
		strings.EqualFold(filepath.Ext(os.Args[1]), ".exe") {

		// arg đầu là exe
		target = os.Args[1]
		args = append(args, os.Args[2:]...)

	} else {
		// mặc định chạy %USERPROFILE%\.local\bin\claude.exe
		home, err := os.UserHomeDir()
		if err != nil {
			os.Exit(1)
		}

		target = filepath.Join(home, ".local", "bin", "claude.exe")
		args = append(args, os.Args[1:]...)
	}

	args = append(args,
		"--disallowedTools",
		disallowedTools,
	)

	cmd := exec.Command(target, args...)
	cmd.SysProcAttr = &syscall.SysProcAttr{
		HideWindow: true,
	}

	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err := cmd.Run()
	if err == nil {
		os.Exit(0)
	}

	if exitErr, ok := err.(*exec.ExitError); ok {
		if ws, ok := exitErr.Sys().(syscall.WaitStatus); ok {
			os.Exit(ws.ExitStatus())
		}
	}

	os.Exit(1)
}